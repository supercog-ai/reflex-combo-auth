import reflex as rx

# Make an rx component from the react-oauth google library
class GoogleOAuthProvider(rx.Component):
    library = "@react-oauth/google"
    tag = "GoogleOAuthProvider"

    client_id: rx.Var[str]

# Crazy ass GoogleLogin button: https://github.com/orgs/reflex-dev/discussions/2621
class GoogleLoginButton(rx.chakra.Button):
    @classmethod
    def create(cls, **props):
        return super().create(
            rx.chakra.image(src="https://logo.clearbit.com/google.com", width="20px", height="20px", margin_right="8px"),
            " Sign in with Google", 
            **props
        )

    def _get_imports(self) -> rx.utils.imports.ImportDict:
        return rx.utils.imports.merge_imports(
            super()._get_imports(),
            {
                "@react-oauth/google": {rx.utils.imports.ImportVar(tag="useGoogleLogin")}
            },
        )

    def _get_hooks(self) -> str | None:
        return """
const myg_login = useGoogleLogin({
  onSuccess: codeResponse => %s(codeResponse),
  flow: 'auth-code',
});""" % self.event_triggers["on_success"]

    def _render(self):
        """Remove the onSuccess prop so that it doesn't try to render to the DOM."""
        tag = super()._render()
        tag.remove_props("onSuccess")
        
        tag.add_props(on_click=rx.vars.BaseVar(_var_name="myg_login", _var_type=rx.event.EventChain))
        return tag

    def get_event_triggers(self):
        return {"on_success": lambda data: [data]}
    
# Return a button inside the GoogleOAuthProvider    
def get_google_login_button(client_id: str, on_success: rx.EventHandler) -> rx.Component:
    return GoogleOAuthProvider.create(
        GoogleLoginButton.create(
            on_success=on_success,
            size="lg",
            width="300px",
        ),
        client_id=client_id,
    )

